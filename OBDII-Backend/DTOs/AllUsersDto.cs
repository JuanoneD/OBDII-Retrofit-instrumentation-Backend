using System.ComponentModel.DataAnnotations;
using ObdII.DTOs;

namespace ObdII.DTOs;

public record AllUsersDto(
    [Required] IEnumerable<UserResponseDto> UsersList,
    [Required] int TotalCount
);