using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ObdII.DTOs;
using ObdII.Services.Interfaces;

namespace ObdII.Controllers;

[ApiController]
[Route("devices")]
[Authorize]
public class DevicesController : ControllerBase
{
    private readonly IVehicleService _vehicleService;
    private readonly IAuthorizationService _authorizationService;

    public DevicesController(IVehicleService vehicleService, IAuthorizationService authorizationService)
    {
        _vehicleService = vehicleService;
        _authorizationService = authorizationService;
    }

    // GET /devices?idDevice=1
    [HttpGet]
    public async Task<IActionResult> Get([FromQuery] string? idDevice)
    {
        var result = await _vehicleService.GetDevicesAsync(GetUserId(), await IsAdminAsync(), idDevice);
        return result is null ? NotFound(new { message = "ESP não encontrada" }) : Ok(result);
    }

    // POST /devices/AABBCC112233  (called by the ESP, without token)
    [AllowAnonymous]
    [HttpPost("{idDevice}")]
    public async Task<IActionResult> Sync(string idDevice, [FromBody] DeviceSyncRequestDto request)
    {
        try
        {
            return Ok(await _vehicleService.SyncAsync(idDevice, request));
        }
        catch (ArgumentException ex)
        {
            return BadRequest(new { message = ex.Message });
        }
    }

    // POST /devices/resetAndRecalculate?idDevice=1
    [HttpPost("resetAndRecalculate")]
    public async Task<IActionResult> ResetAndRecalculate(
        [FromQuery] string idDevice, [FromBody] ResetAndRecalculateDto request)
    {
        try
        {
            var result = await _vehicleService.ResetAndRecalculateAsync(
                idDevice, GetUserId(), await IsAdminAsync(), request);
            return result is null ? NotFound(new { message = "ESP não encontrada" }) : Ok(result);
        }
        catch (ArgumentException ex)
        {
            return BadRequest(new { message = ex.Message });
        }
    }

    // POST /devices/resetTrip?idDevice=1
    [HttpPost("resetTrip")]
    public async Task<IActionResult> ResetTrip([FromQuery] string idDevice)
    {
        var result = await _vehicleService.ResetTripAsync(idDevice, GetUserId(), await IsAdminAsync());
        return result is null ? NotFound(new { message = "ESP não encontrada" }) : Ok(result);
    }

    // Reuses the "AdminOnly" policy already used in UserController
    private async Task<bool> IsAdminAsync()
        => (await _authorizationService.AuthorizeAsync(User, "AdminOnly")).Succeeded;

    // Adjust the claim according to what is set in the JWT at login.
    private int GetUserId()
    {
        var value = User.FindFirstValue(ClaimTypes.NameIdentifier) ?? User.FindFirstValue("sub");
        return int.Parse(value!);
    }
}