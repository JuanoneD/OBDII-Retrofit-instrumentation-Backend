import re

from django.core.exceptions import ValidationError
from django.db import models

MAC_REGEX = re.compile(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$")


def normalize_device_id(value):
    """Padroniza o MAC da ESP32: 'aa-bb-cc-dd-ee-ff' ou 'aabbccddeeff' -> 'AA:BB:CC:DD:EE:FF'."""
    raw = re.sub(r"[^0-9A-Fa-f]", "", str(value or "")).upper()
    if len(raw) != 12:
        return str(value or "").strip().upper()
    return ":".join(raw[i : i + 2] for i in range(0, 12, 2))


def validate_device_id(value):
    if not MAC_REGEX.match(normalize_device_id(value)):
        raise ValidationError("device_id deve ser o MAC da ESP32, ex.: AA:BB:CC:DD:EE:FF")


class Vehicle(models.Model):
    """
    Um veículo com uma ESP32 instalada (BE-05).

    Guarda também o estado "persistente" do combustível, que na ESP32 fica
    salvo na memória NVS e é atualizado a cada envio (BE-02).
    """

    # Identificador único da ESP32 = endereço MAC (BE-05)
    device_id = models.CharField(
        "ID do dispositivo (MAC)", max_length=17, unique=True, validators=[validate_device_id]
    )
    name = models.CharField("apelido do veículo", max_length=100)
    plate = models.CharField("placa", max_length=10, blank=True)
    model = models.CharField("modelo", max_length=100, blank=True)
    owner_name = models.CharField("nome do dono", max_length=100, blank=True)
    is_active = models.BooleanField("ativo", default=True)

    # --- Estado persistente do combustível (espelha a NVS da ESP32) ---
    tank_capacity = models.FloatField("capacidade do tanque (L)", default=45.0)
    gasoline_level = models.FloatField("nível de gasolina (L)", default=45.0)
    fuel_consumption_factor = models.FloatField("fator de consumo (K)", default=0.008)
    total_distance = models.FloatField("distância total (km)", default=0.0)
    trip_consumption = models.FloatField(
        "litros gastos no sistema desde o último abastecimento", default=0.0
    )

    # Sincronização backend -> ESP32 (após um recálculo do fator no BE-04):
    # o backend aumenta sync_version; a ESP32 aplica os valores novos e passa
    # a enviar esse mesmo número em "sync_version", confirmando que aplicou.
    sync_version = models.PositiveIntegerField("versão dos dados no backend", default=0)
    esp_sync_version = models.PositiveIntegerField("versão confirmada pela ESP32", default=0)

    last_seen_at = models.DateTimeField("último envio recebido", null=True, blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "veículo"
        verbose_name_plural = "veículos"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.device_id})"

    def save(self, *args, **kwargs):
        self.device_id = normalize_device_id(self.device_id)
        super().save(*args, **kwargs)

    @property
    def pending_sync(self):
        """True quando existe um recálculo que a ESP32 ainda não aplicou."""
        return self.sync_version > self.esp_sync_version

    def sync_payload(self):
        """Valores que a ESP32 deve gravar na NVS dela (ou None se não há nada novo)."""
        if not self.pending_sync:
            return None
        return {
            "sync_version": self.sync_version,
            "fuel_consumption_factor": self.fuel_consumption_factor,
            "gasoline_level": self.gasoline_level,
            "trip_consumption": self.trip_consumption,
        }

    @property
    def fuel_percent(self):
        if not self.tank_capacity:
            return 0.0
        return round(self.gasoline_level / self.tank_capacity * 100, 1)


class Reading(models.Model):
    """Uma leitura enviada pela ESP32 (histórico para o dashboard e gráficos)."""

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="readings")

    # Chave de tempo: quando a ESP32 enviou (se ela souber a hora) e quando chegou.
    sent_at = models.DateTimeField("enviado em", db_index=True)
    received_at = models.DateTimeField("recebido em", auto_now_add=True)

    # --- Campos voláteis (tempo real) ---
    rpm = models.IntegerField("RPM")
    speed = models.IntegerField("velocidade (km/h)")
    coolant_temp = models.IntegerField("temperatura do arrefecimento (°C)")
    engine_load = models.FloatField("carga do motor (%)")
    throttle_position = models.FloatField("posição do acelerador (%)")
    ltft = models.FloatField("LTFT - correção de combustível de longo prazo (%)")
    timing_advance = models.FloatField("avanço de ignição (°)", null=True, blank=True)
    module_voltage = models.FloatField("tensão do módulo (V)", null=True, blank=True)
    map_pressure = models.FloatField("pressão MAP (kPa)", null=True, blank=True)

    # Foto do combustível no momento da leitura (para gráfico de nível)
    gasoline_level = models.FloatField("nível de gasolina (L)")
    fuel_percent = models.FloatField("combustível (%)")

    class Meta:
        verbose_name = "leitura"
        verbose_name_plural = "leituras"
        ordering = ["-sent_at", "-id"]
        indexes = [models.Index(fields=["vehicle", "-sent_at"])]

    def __str__(self):
        return f"{self.vehicle.name} @ {self.sent_at:%d/%m/%Y %H:%M:%S}"
