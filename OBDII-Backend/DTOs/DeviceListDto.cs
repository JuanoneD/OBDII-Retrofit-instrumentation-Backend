using System.Text.Json.Serialization;

namespace ObdII.DTOs;

public record DeviceListDto(
    [property: JsonPropertyName("device")] IEnumerable<DeviceDto> Device,
    [property: JsonPropertyName("totalDevice")] int TotalDevice
);