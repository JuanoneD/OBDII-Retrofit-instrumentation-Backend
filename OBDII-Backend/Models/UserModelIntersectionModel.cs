namespace ObdII.Models;

public class UserModelIntersectionModel
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public UserModel User { get; set; }
    public string VehicleId { get; set; } = string.Empty;
    public VehicleModel Vehicle { get; set; }
}
