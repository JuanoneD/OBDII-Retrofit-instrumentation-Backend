using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ObdII.DTOs;
using ObdII.Services.Interfaces;

namespace ObdII.Controllers;

[ApiController]
[Route("user")]
public class UserController : ControllerBase
{
    private readonly IUserService _userService;

    public UserController(IUserService userService)
    {
        _userService = userService;
    }

    [HttpGet]
    [Authorize(Policy = "AdminOnly")]
    public async Task<IActionResult> GetAll()
        => Ok(await _userService.GetAllUsersAsync());

    [HttpPost]
    public async Task<IActionResult> Create(CreateUserDto dto)
    {
        try { return Ok(await _userService.CreateAccountAsync(dto)); }
        catch (InvalidOperationException) { return Conflict(); }
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login(LoginDto dto)
    {
        try { return Ok(await _userService.Login(dto)); }
        catch (UnauthorizedAccessException) { return Unauthorized(); }
    }

    [HttpPost("logout")]
    [Authorize]
    public async Task<IActionResult> Logout()
    {
        var token = Request.Headers.Authorization.ToString().Replace("Bearer ", "");
        await _userService.Logout(new TokenDto(token));
        return Ok();
    }
}