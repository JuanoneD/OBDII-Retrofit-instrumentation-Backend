using Microsoft.EntityFrameworkCore;

namespace ObdII.Models;

public class ObdIIContext : DbContext
{
    public ObdIIContext(DbContextOptions<ObdIIContext> options) : base(options)
    {
    }
    public DbSet<UserModel> Users { get; set; }
    public DbSet<VehicleModel> Vehicles { get; set; }
    public DbSet<UserModelIntersectionModel> UserVehicleIntersections { get; set; }
}
