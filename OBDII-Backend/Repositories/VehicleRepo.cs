using Microsoft.EntityFrameworkCore;
using ObdII.Models;
using ObdII.Repositories.Interfaces;

namespace ObdII.Repositories;

public class VehicleRepository : IVehicleRepository
{
    private readonly ObdIIContext _context;

    public VehicleRepository(ObdIIContext context)
    {
        _context = context;
    }

    public async Task<IEnumerable<VehicleModel>> GetAllAsync()
    {
        return await _context.Vehicles
            .AsNoTracking()
            .ToListAsync();
    }

    public async Task<VehicleModel?> GetByIdAsync(string id)
    {
        return await _context.Vehicles
            .AsNoTracking()
            .FirstOrDefaultAsync(v => v.Id == id);
    }

    public async Task<VehicleModel> AddAsync(VehicleModel vehicle)
    {
        _context.Vehicles.Add(vehicle);
        await _context.SaveChangesAsync();
        return vehicle;
    }

    public async Task<VehicleModel> UpdateAsync(VehicleModel vehicle)
    {
        _context.Vehicles.Update(vehicle);
        await _context.SaveChangesAsync();
        return vehicle;
    }

    public async Task<IEnumerable<VehicleModel>> GetByUserIdAsync(int userId)
    {
        return await _context.UserVehicleIntersections
            .AsNoTracking()
            .Where(i => i.UserId == userId)
            .Select(i => i.Vehicle)
            .ToListAsync();
    }

    public async Task LinkToUserAsync(int userId, string vehicleId)
    {
        var alreadyLinked = await _context.UserVehicleIntersections
            .AnyAsync(i => i.UserId == userId && i.VehicleId == vehicleId);
        if (alreadyLinked)
            return;

        _context.UserVehicleIntersections.Add(new UserModelIntersectionModel
        {
            UserId = userId,
            VehicleId = vehicleId
        });
        await _context.SaveChangesAsync();
    }

    public async Task<bool> DeleteAsync(string id)
    {
        var vehicle = await _context.Vehicles.FindAsync(id);
        if (vehicle is null)
            return false;

        var links = _context.UserVehicleIntersections.Where(i => i.VehicleId == id);
        _context.UserVehicleIntersections.RemoveRange(links);

        _context.Vehicles.Remove(vehicle);
        await _context.SaveChangesAsync();
        return true;
    }
}   