using Microsoft.EntityFrameworkCore;
using ObdII.Models;
using ObdII.Repositories.Interfaces;

namespace ObdII.Repositories;

public class RevokedTokenRepository : IRevokedTokenRepository
{
    private readonly ObdIIContext _context;

    public RevokedTokenRepository(ObdIIContext context)
    {
        _context = context;
    }

    public async Task AddAsync(string jti, DateTime expiresAt)
    {
        if (await IsRevokedAsync(jti)) return;

        _context.RevokedTokens.Add(new RevokedTokenModel
        {
            Jti = jti,
            ExpiresAt = expiresAt
        });
        await _context.SaveChangesAsync();
    }

    public async Task<bool> IsRevokedAsync(string jti)
        => await _context.RevokedTokens.AsNoTracking().AnyAsync(t => t.Jti == jti);

    public async Task<int> DeleteExpiredAsync()
        => await _context.RevokedTokens
            .Where(t => t.ExpiresAt < DateTime.UtcNow)
            .ExecuteDeleteAsync();
}