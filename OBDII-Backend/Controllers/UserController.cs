using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ObdII.DTOs;
using ObdII.Services.Interfaces;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;

namespace ObdII.Controllers;

[ApiController]
[Route("user")]
public class UserController : ControllerBase
{
    private readonly IUserService _userService;
    private readonly IVehicleService _vehicleService;

    public UserController(IUserService userService, IVehicleService vehicleService)
    {
        _userService = userService;
        _vehicleService = vehicleService;
    }

    [HttpPost("addDevice")]
    [Authorize]
    public async Task<IActionResult> AddDevice(AddDeviceDto dto)
    {
        var userId = int.Parse(User.FindFirstValue(ClaimTypes.NameIdentifier)
                            ?? User.FindFirstValue(JwtRegisteredClaimNames.Sub)!);
        try
        {
            var found = await _vehicleService.AddDeviceToUserAsync(userId, dto.IdDevice);
            return found ? Ok() : NotFound(new { message = "ESP não encontrada" });
        }
        catch (ArgumentException ex) { return BadRequest(new { message = ex.Message }); }
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