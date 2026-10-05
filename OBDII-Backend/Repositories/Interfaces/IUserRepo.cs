using ObdII.Models;

namespace ObdII.Repositories.Interfaces;

public interface IUserRepository
{
    Task<IEnumerable<UserModel>> GetAllAsync();
    Task<UserModel?> GetByIdAsync(int id);
    Task<UserModel> AddAsync(UserModel user);
    Task<UserModel> UpdateAsync(UserModel user);
    Task<bool> DeleteAsync(int id);
    Task<UserModel?> GetByEmailAsync(string email);

}