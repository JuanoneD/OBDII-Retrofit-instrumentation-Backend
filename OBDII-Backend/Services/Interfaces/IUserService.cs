using ObdII.Models;
using ObdII.DTOs;

namespace ObdII.Services.Interfaces;

public interface IUserService
{
    // return Token for login
    Task<TokenDto> CreateAccountAsync(CreateUserDto userData);

    Task<TokenDto> Login(LoginDto loginData);

    Task<bool> Logout(TokenDto tokenData);

    Task<AllUsersDto> GetAllUsersAsync();
}
