using System.ComponentModel.DataAnnotations;

namespace ObdII.DTOs;

public record UserResponseDto
(
    [Required] int Id,
    [Required] string Username,
    [Required] string Email
);