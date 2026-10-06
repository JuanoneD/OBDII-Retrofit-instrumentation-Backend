namespace ObdII.Models;

public class VehicleModel
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;

    public float GasLevel { get; set; }

    public float TankCapacity { get; set; }

    public float FuelConsumptionFactor { get; set; }

    public float TripTotalDistance { get; set; }

    public float TripConsumption { get; set; }

    public int SyncVersion { get; set; }
}