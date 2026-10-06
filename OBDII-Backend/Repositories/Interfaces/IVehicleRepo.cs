using ObdII.Models;

namespace ObdII.Repositories.Interfaces;

public interface IVehicleRepository
{
    Task<IEnumerable<VehicleModel>> GetAllAsync();
    Task<VehicleModel?> GetByIdAsync(string id);
    Task<VehicleModel> AddAsync(VehicleModel vehicle);
    Task<VehicleModel> UpdateAsync(VehicleModel vehicle);

    Task<IEnumerable<VehicleModel>> GetByUserIdAsync(int userId);

    // Links the ESP to the user (does not duplicate if already linked)
    Task LinkToUserAsync(int userId, string vehicleId);

    Task<bool> DeleteAsync(string id);
}