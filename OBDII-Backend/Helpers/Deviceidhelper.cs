namespace ObdII.Helpers;

public static class DeviceIdHelper
{
    // Standardizes the ESP MAC: "aa:bb:cc:11:22:33" / "AA-BB-CC-11-22-33" -> "AABBCC112233"
    public static string Normalize(string deviceId)
        => deviceId.Trim().Replace(":", "").Replace("-", "").ToUpperInvariant();

    // Normalized MAC: exactly 12 hexadecimal characters
    public static bool IsValid(string normalizedId)
        => normalizedId.Length == 12 && normalizedId.All(Uri.IsHexDigit);
}