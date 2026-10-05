namespace ObdII.Repositories.Interfaces;

public interface IRevokedTokenRepository
{
    Task AddAsync(string jti, DateTime expiresAt);
    Task<bool> IsRevokedAsync(string jti);
    Task<int> DeleteExpiredAsync();
}