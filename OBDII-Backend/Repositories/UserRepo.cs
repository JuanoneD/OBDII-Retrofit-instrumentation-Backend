using Microsoft.EntityFrameworkCore;
using ObdII.Models;
using ObdII.Repositories.Interfaces;

namespace ObdII.Repositories;

public class UserRepository : IUserRepository
{
    private readonly ObdIIContext _context;

    public UserRepository(ObdIIContext context)
    {
        _context = context;
    }

    public async Task<IEnumerable<UserModel>> GetAllAsync()
        => await _context.Users.AsNoTracking().ToListAsync();

    public async Task<UserModel?> GetByIdAsync(int id)
        => await _context.Users.FindAsync(id);

    public async Task<UserModel> AddAsync(UserModel user)
    {
        _context.Users.Add(user);
        await _context.SaveChangesAsync();
        return user;
    }

    public async Task<UserModel> UpdateAsync(UserModel user)
    {
        _context.Users.Update(user);
        await _context.SaveChangesAsync();
        return user;
    }

    public async Task<bool> DeleteAsync(int id)
    {
        var user = await _context.Users.FindAsync(id);
        if (user is null) return false;

        _context.Users.Remove(user);
        await _context.SaveChangesAsync();
        return true;
    }
    
    public async Task<UserModel?> GetByEmailAsync(string email)
    => await _context.Users.AsNoTracking()
        .FirstOrDefaultAsync(u => u.Email == email);
}