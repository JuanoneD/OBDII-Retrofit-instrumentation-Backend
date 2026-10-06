using ObdII.DTOs;
using ObdII.Helpers;
using ObdII.Models;
using ObdII.Repositories.Interfaces;
using ObdII.Services.Interfaces;

namespace ObdII.Services;

public class VehicleService : IVehicleService
{
    private readonly IVehicleRepository _vehicleRepository;

    public VehicleService(IVehicleRepository vehicleRepository)
    {
        _vehicleRepository = vehicleRepository;
    }

    public async Task<DeviceListDto?> GetDevicesAsync(int userId, bool isAdmin, string? deviceId)
    {
        if (!string.IsNullOrWhiteSpace(deviceId))
        {
            var vehicle = await GetAccessibleAsync(DeviceIdHelper.Normalize(deviceId), userId, isAdmin);
            if (vehicle is null)
                return null;

            return new DeviceListDto(new[] { ToDto(vehicle) }, 1);
        }

        var vehicles = isAdmin
            ? await _vehicleRepository.GetAllAsync()
            : await _vehicleRepository.GetByUserIdAsync(userId);

        var devices = vehicles.Select(ToDto).ToList();
        return new DeviceListDto(devices, devices.Count);
    }

    public async Task<DeviceDto> SyncAsync(string deviceId, DeviceSyncRequestDto request)
    {
        var id = DeviceIdHelper.Normalize(deviceId);
        if (!DeviceIdHelper.IsValid(id))
            throw new ArgumentException("idDevice inválido: esperado MAC com 12 caracteres hexadecimais.");

        var vehicle = await _vehicleRepository.GetByIdAsync(id);

        // First time the ESP appears: register it, even without a linked user.
        if (vehicle is null)
        {
            vehicle = await _vehicleRepository.AddAsync(new VehicleModel
            {
                Id = id,
                Name = string.Empty,
                GasLevel = request.GasolineLevel,
                TankCapacity = request.TankCapacity,
                FuelConsumptionFactor = request.FuelConsumptionFactor,
                TripTotalDistance = request.TotalDistance,
                TripConsumption = request.TripConsumption,
                SyncVersion = 0
            });
            return ToDto(vehicle);
        }

        // Only accept data from the ESP if it is on the same version as the database.
        // If different, the backend changed (reset/recalculation) and the ESP must
        // overwrite its internal values with those returned in the response.
        if (request.SyncVersion == vehicle.SyncVersion)
        {
            vehicle.GasLevel = request.GasolineLevel;
            vehicle.TankCapacity = request.TankCapacity;
            vehicle.FuelConsumptionFactor = request.FuelConsumptionFactor;
            vehicle.TripTotalDistance = request.TotalDistance;
            vehicle.TripConsumption = request.TripConsumption;

            vehicle = await _vehicleRepository.UpdateAsync(vehicle);
        }

        return ToDto(vehicle);
    }

    public async Task<DeviceDto?> ResetAndRecalculateAsync(
        string deviceId, int userId, bool isAdmin, ResetAndRecalculateDto request)
    {
        if (request.RefueledGas <= 0)
            throw new ArgumentException("refueledGas deve ser maior que zero.");

        var vehicle = await GetAccessibleAsync(DeviceIdHelper.Normalize(deviceId), userId, isAdmin);
        if (vehicle is null)
            return null;

        // New Factor = Old Factor * (Refueled Liters / System Spent Liters)
        // System spent liters = what the system calculates was consumed from the tank.
        // If the system registered no consumption, keep the current factor (prevents division by zero).
        var litersSpentBySystem = vehicle.TankCapacity - vehicle.GasLevel;
        if (litersSpentBySystem > 0)
            vehicle.FuelConsumptionFactor *= request.RefueledGas / litersSpentBySystem;

        vehicle.GasLevel = vehicle.TankCapacity;
        vehicle.SyncVersion++; // forces the ESP to adopt the database values

        vehicle = await _vehicleRepository.UpdateAsync(vehicle);
        return ToDto(vehicle);
    }

    public async Task<DeviceDto?> ResetTripAsync(string deviceId, int userId, bool isAdmin)
    {
        var vehicle = await GetAccessibleAsync(DeviceIdHelper.Normalize(deviceId), userId, isAdmin);
        if (vehicle is null)
            return null;

        vehicle.TripTotalDistance = 0;
        vehicle.TripConsumption = 0;
        vehicle.SyncVersion++;

        vehicle = await _vehicleRepository.UpdateAsync(vehicle);
        return ToDto(vehicle);
    }

    public async Task<bool> AddDeviceToUserAsync(int userId, string deviceId)
    {
        var id = DeviceIdHelper.Normalize(deviceId);
        if (!DeviceIdHelper.IsValid(id))
            throw new ArgumentException("idDevice inválido: esperado MAC com 12 caracteres hexadecimais.");

        // The ESP must have registered beforehand (first POST /devices/{idDevice})
        var vehicle = await _vehicleRepository.GetByIdAsync(id);
        if (vehicle is null)
            return false;

        await _vehicleRepository.LinkToUserAsync(userId, id);
        return true;
    }

    // Admin accesses any ESP; regular users only access those linked to them.
    // If it does not belong to the user, treat as "not found" to avoid revealing its existence.
    private async Task<VehicleModel?> GetAccessibleAsync(string deviceId, int userId, bool isAdmin)
    {
        if (isAdmin)
            return await _vehicleRepository.GetByIdAsync(deviceId);

        var userVehicles = await _vehicleRepository.GetByUserIdAsync(userId);
        return userVehicles.FirstOrDefault(v => v.Id == deviceId);
    }

    private static DeviceDto ToDto(VehicleModel v) => new(
        v.Id,
        v.Name,
        v.GasLevel,
        v.TankCapacity,
        v.FuelConsumptionFactor,
        v.TripTotalDistance,
        v.TripConsumption,
        v.SyncVersion);
}