namespace ObdII.Models;

public class VehicleModel
{
    public int Id { get; set; }
    public string Name { get; set; }

    public float GasLevel { get; set; }

    public float TankCapacity { get; set; }

    public float FuelConsumptionFactor { get; set; }

    public float TripTotalDistance { get; set; }

    public float TripConsumption { get; set; }
}