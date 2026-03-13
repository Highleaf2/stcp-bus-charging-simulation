"""
Enviar Telemetria Estática para Azure
Apenas envia valores fixos - algoritmo será criado no Databricks
"""

import asyncio
import json
from datetime import datetime
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import Message
import config

# Valores FIXOS para enviar
STATIC_DATA = {
    "BUS-001": {
        "batteryKwh": 105.0,
        "batteryLevel": 30.0,
        "batteryTemperature": 22.5,
        "latitude": 41.157713,
        "longitude": -8.679766,
        "state": "ROUTE"
    },
    "BUS-002": {
        "batteryKwh": 245.0,
        "batteryLevel": 70.0,
        "batteryTemperature": 21.8,
        "latitude": 41.151033,
        "longitude": -8.610854,
        "state": "ROUTE"
    },
    "BUS-003": {
        "batteryKwh": 87.5,
        "batteryLevel": 25.0,
        "batteryTemperature": 20.2,
        "latitude": 41.148820,
        "longitude": -8.672750,
        "state": "IDLE_DEPOT"
    },
    "CS-001": {
        "chargerTemperature": 25.0,
        "currentEfficiency": 92.0,
        "currentPower": 0.0,
        "energyDelivered": 0.0,
        "state": "IDLE",
        "connectedBus": None,
        "totalEnergyDelivered": 0.0,
        "latitude": 41.183580,
        "longitude": -8.618978
    },
    "CS-002": {
        "chargerTemperature": 24.5,
        "currentEfficiency": 91.5,
        "currentPower": 0.0,
        "energyDelivered": 0.0,
        "state": "IDLE",
        "connectedBus": None,
        "totalEnergyDelivered": 0.0,
        "latitude": 41.183580,
        "longitude": -8.618978
    },
    "CS-003": {
        "chargerTemperature": 25.2,
        "currentEfficiency": 93.0,
        "currentPower": 0.0,
        "energyDelivered": 0.0,
        "state": "IDLE",
        "connectedBus": None,
        "totalEnergyDelivered": 0.0,
        "latitude": 41.183580,
        "longitude": -8.618978
    }
}

async def provision_device(device_id):
    """Provisionar dispositivo no Azure IoT Central"""
    try:
        device_key = config.get_device_key(device_id)
        
        provisioning_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host=config.PROVISIONING_HOST,
            registration_id=device_id,
            id_scope=config.ID_SCOPE,
            symmetric_key=device_key
        )
        
        print(f"[{device_id}] A registar...")
        registration_result = await provisioning_client.register()
        
        if registration_result.status == "assigned":
            print(f"[{device_id}] ✓ Registado")
            
            conn_str = f"HostName={registration_result.registration_state.assigned_hub};DeviceId={device_id};SharedAccessKey={device_key}"
            client = IoTHubDeviceClient.create_from_connection_string(conn_str)
            await client.connect()
            
            return client
        else:
            print(f"[{device_id}] ✗ Falhou: {registration_result.status}")
            return None
            
    except Exception as e:
        print(f"[{device_id}] ✗ Erro: {e}")
        return None

async def send_telemetry(client, device_id, telemetry):
    """Enviar telemetria para IoT Central"""
    try:
        message = Message(json.dumps(telemetry))
        message.content_encoding = "utf-8"
        message.content_type = "application/json"
        await client.send_message(message)
    except Exception as e:
        print(f"[{device_id}] Erro ao enviar: {e}")

async def main():
    """Enviar telemetria estática continuamente"""
    print("="*80)
    print("ENVIO DE TELEMETRIA ESTÁTICA PARA AZURE")
    print("Valores fixos - Algoritmo será criado no Databricks")
    print("="*80)
    
    # Provisionar todos os dispositivos
    clients = {}
    for device_id in STATIC_DATA.keys():
        client = await provision_device(device_id)
        if client:
            clients[device_id] = client
    
    print(f"\n✓ {len(clients)} dispositivos conectados\n")
    
    print("VALORES A ENVIAR:")
    print("-"*80)
    for device_id, data in STATIC_DATA.items():
        if "batteryLevel" in data:
            print(f"{device_id}: Bateria {data['batteryLevel']:.1f}%, Estado: {data['state']}")
        else:
            print(f"{device_id}: {data['state']}")
    print("-"*80)
    
    print("\n>>> A ENVIAR TELEMETRIA A CADA 10 SEGUNDOS <<<")
    print(">>> Pressiona CTRL+C para parar <<<\n")
    
    try:
        counter = 0
        while True:
            counter += 1
            
            # Enviar telemetria de todos os dispositivos
            for device_id, client in clients.items():
                telemetry = STATIC_DATA[device_id]
                await send_telemetry(client, device_id, telemetry)
            
            # Log a cada 60 segundos
            if counter % 6 == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Enviado ciclo {counter // 6}")
            
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\nA parar...")
    finally:
        # Desconectar
        for device_id, client in clients.items():
            await client.disconnect()
            print(f"[{device_id}] Desconectado")

if __name__ == "__main__":
    asyncio.run(main())
