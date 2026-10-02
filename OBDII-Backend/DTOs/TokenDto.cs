using System.ComponentModel.DataAnnotations;

namespace ObdII.DTOs;

public record TokenDto(
    [Required] string Token
);