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

    public DbSet<RevokedTokenModel> RevokedTokens { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<RevokedTokenModel>(entity =>
        {
            entity.HasIndex(t => t.Jti).IsUnique();
            entity.HasIndex(t => t.ExpiresAt);
            entity.Property(t => t.Jti).HasMaxLength(64);
        });
    }
}
