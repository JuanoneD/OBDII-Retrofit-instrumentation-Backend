using System.ComponentModel.DataAnnotations;

namespace ObdII.DTOs;

public record CreateUserDto(
    [Required] string Username,
    [Required] string Email,
    [Required] string Password
);