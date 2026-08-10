from decimal import Decimal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Import corretti basati sul tuo sorgente
from inc_tax_sim.domain.services.net_salary_calculator import CalcolaNettoService
from inc_tax_sim.domain.value_objects.fiscal_regime import REGIME_2026_MILANO

app = FastAPI(
    title="Net Salary Calculator API", 
    description="API per calcolare il netto partendo dalla RAL",
    version="0.1.0"
)

# --- DTO DI INPUT BLINDATO ---
# Usiamo Decimal per matchare al 100% l'input richiesto dal tuo dominio
class RalRequest(BaseModel):
    ral: Decimal = Field(..., gt=0, description="Retribuzione Annua Lorda (deve essere > 0)")

# --- ENDPOINT ---
@app.post("/api/v1/net-salary")
async def calculate_net_salary(payload: RalRequest):
    try:
        # Istanziamo il servizio DENTRO l'endpoint.
        # Così in futuro potrai iniettare il regime dinamico in base all'input.
        calculator = CalcolaNettoService(REGIME_2026_MILANO)
        
        # Passiamo direttamente il Decimal al dominio
        net_salary_dto = calculator.calcola(ral=payload.ral)

        # FastAPI serializzerà in automatico la tua dataclass RisultatoNetto
        return {
            "status": "success",
            "data": net_salary_dto 
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    