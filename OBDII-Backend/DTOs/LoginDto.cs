using System.ComponentModel.DataAnnotations;

namespace ObdII.DTOs;

public record LoginDto(
    [Required] string Email,
    [Required] string Password
);