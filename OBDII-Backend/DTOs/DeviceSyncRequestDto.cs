using System.Text.Json.Serialization;

namespace ObdII.DTOs;

public record DeviceSyncRequestDto(
    float GasolineLevel,
    float TankCapacity,
    float FuelConsumptionFactor,
    float TotalDistance,
    float TripConsumption,
    [property: JsonPropertyName("sync_version")] int SyncVersion
);