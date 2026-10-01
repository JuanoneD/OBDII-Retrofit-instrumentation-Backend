namespace ObdII.Models;

public class UserModelIntersectionModel
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public UserModel User { get; set; }
    public int VehicleId { get; set; }
    public VehicleModel Vehicle { get; set; }
}