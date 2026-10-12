using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace ObdII.DTOs;

public record AddDeviceDto(
    [property: JsonPropertyName("idDevice")] string IdDevice,
    [property: JsonPropertyName("name")] string? Name = null
);
