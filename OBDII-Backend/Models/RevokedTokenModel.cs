namespace ObdII.Models;

public class RevokedTokenModel
{
    public int Id { get; set; }
    public string Jti { get; set; } = string.Empty;
    public DateTime ExpiresAt { get; set; }
}