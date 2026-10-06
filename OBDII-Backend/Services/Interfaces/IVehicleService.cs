using ObdII.DTOs;

namespace ObdII.Services.Interfaces;

public interface IVehicleService
{
    // null => ESP not found (404). Without deviceId => list (empty if none exist).
    Task<DeviceListDto?> GetDevicesAsync(int userId, bool isAdmin, string? deviceId);

    // Creates the ESP on the first POST. Throws ArgumentException if the MAC is invalid (400).
    Task<DeviceDto> SyncAsync(string deviceId, DeviceSyncRequestDto request);

    // null => ESP not found (404). Throws ArgumentException if refueledGas <= 0 (400).
    Task<DeviceDto?> ResetAndRecalculateAsync(string deviceId, int userId, bool isAdmin, ResetAndRecalculateDto request);

    // null => ESP not found (404)
    Task<DeviceDto?> ResetTripAsync(string deviceId, int userId, bool isAdmin);

    // false => ESP not found (404). Throws ArgumentException if the MAC is invalid (400).
    Task<bool> AddDeviceToUserAsync(int userId, string deviceId);
}