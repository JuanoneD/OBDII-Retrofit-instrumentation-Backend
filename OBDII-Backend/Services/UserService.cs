using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.AspNetCore.Identity;
using Microsoft.IdentityModel.Tokens;
using ObdII.DTOs;
using ObdII.Models;
using ObdII.Repositories.Interfaces;
using ObdII.Services.Interfaces;

namespace ObdII.Services;

public class UserService : IUserService
{
    private readonly IUserRepository _userRepository;
    private readonly IRevokedTokenRepository _revokedTokenRepository;
    private readonly IConfiguration _config;
    private readonly PasswordHasher<UserModel> _passwordHasher = new();

    public UserService(
        IUserRepository userRepository,
        IRevokedTokenRepository revokedTokenRepository,
        IConfiguration config)
    {
        _userRepository = userRepository;
        _revokedTokenRepository = revokedTokenRepository;
        _config = config;
    }

    public async Task<TokenDto> CreateAccountAsync(CreateUserDto userData)
    {
        var existing = await _userRepository.GetByEmailAsync(userData.Email);
        if (existing is not null)
            throw new InvalidOperationException("Email já cadastrado.");

        var user = new UserModel
        {
            Username = userData.Username,
            Email = userData.Email
        };
        user.Password = _passwordHasher.HashPassword(user, userData.Password);

        await _userRepository.AddAsync(user);

        // criou a conta, já devolve o token (logado automaticamente)
        return new TokenDto(GenerateToken(user));
    }

    public async Task<TokenDto> Login(LoginDto loginData)
    {
        var user = await _userRepository.GetByEmailAsync(loginData.Email);

        // mesma mensagem para email inexistente e senha errada,
        // para não revelar quais emails existem
        if (user is null)
            throw new UnauthorizedAccessException("Email ou senha inválidos.");

        var result = _passwordHasher.VerifyHashedPassword(
            user, user.Password, loginData.Password);

        if (result == PasswordVerificationResult.Failed)
            throw new UnauthorizedAccessException("Email ou senha inválidos.");

        return new TokenDto(GenerateToken(user));
    }

    public async Task<bool> Logout(TokenDto tokenData)
    {
        var handler = new JwtSecurityTokenHandler();

        if (!handler.CanReadToken(tokenData.Token))
            return false;

        var jwt = handler.ReadJwtToken(tokenData.Token);

        // limpa os tokens que já expiraram
        await _revokedTokenRepository.DeleteExpiredAsync();

        // revoga o token atual (se ainda for válido)
        if (jwt.ValidTo > DateTime.UtcNow)
            await _revokedTokenRepository.AddAsync(jwt.Id, jwt.ValidTo);

        return true;
    }

    public async Task<AllUsersDto> GetAllUsersAsync()
    {
        var users = await _userRepository.GetAllAsync();

        var dtos = users
            .Select(u => new UserResponseDto(u.Id, u.Username, u.Email))
            .ToList();

        return new AllUsersDto(dtos, dtos.Count);
    }

    private string GenerateToken(UserModel user)
    {
        var key = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(_config["Jwt:Key"]!));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var claims = new[]
        {
            new Claim(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
            new Claim("IsAdmin", user.IsAdmin.ToString())
        };

        var token = new JwtSecurityToken(
            issuer: _config["Jwt:Issuer"],
            audience: _config["Jwt:Audience"],
            claims: claims,
            expires: DateTime.UtcNow.AddHours(2),
            signingCredentials: creds);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}