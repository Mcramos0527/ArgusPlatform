# app/models.py
# Modelos de datos del sistema ARGUS

from dataclasses import dataclass, field
from typing import Optional
from datetime import date


@dataclass
class Transaction:
    """Modelo unificado de transacción bancaria normalizada."""

    pestaña: str = ""
    empresa: str = ""
    banco: str = ""

    fecha: Optional[date] = None
    fecha_valor: Optional[date] = None

    descripcion: str = ""
    detalle: str = ""

    debito: float = 0.0
    credito: float = 0.0
    importe_neto: float = 0.0   # positivo = ingreso, negativo = egreso
    saldo: float = 0.0

    nro_referencia: str = ""
    nro_cheque: str = ""
    cod_concepto: str = ""
    tipo_concepto: str = ""
    canal: str = ""
    sucursal: str = ""

    categoria_codigo: Optional[int] = None
    categoria_nombre: str = ""
    tipo_movimiento: str = ""   # COBRO / PAGO / INTERNO / SIN CLASIFICAR
    alerta: str = ""               # human error detection alert

    def to_dict(self) -> dict:
        return {
            "Pestaña":           self.pestaña,
            "Empresa":           self.empresa,
            "Banco":             self.banco,
            "Fecha":             self.fecha,
            "Fecha Valor":       self.fecha_valor,
            "Descripción":       self.descripcion,
            "Detalle":           self.detalle,
            "Débito":            self.debito if self.debito else "",
            "Crédito":           self.credito if self.credito else "",
            "Importe Neto":      self.importe_neto,
            "Saldo":             self.saldo,
            "Nro Referencia":    self.nro_referencia,
            "Nro Cheque":        self.nro_cheque,
            "Cod Concepto":      self.cod_concepto,
            "Tipo Concepto":     self.tipo_concepto,
            "Canal":             self.canal,
            "Sucursal":          self.sucursal,
            "Cat. Código":       self.categoria_codigo,
            "Cat. Nombre":       self.categoria_nombre,
            "Tipo Movimiento":   self.tipo_movimiento,
            "Alerta":            self.alerta,
        }


@dataclass
class BankSummary:
    """Resumen diario de una cuenta bancaria — replica BANCOS DEL DIA."""

    empresa: str = ""
    banco: str = ""
    pestaña: str = ""
    saldo_actual: float = 0.0
    gastos_dia: float = 0.0
    intereses_dia: float = 0.0
    cobros_dia: float = 0.0
    pagos_dia: float = 0.0
    movimientos_count: int = 0

    def to_dict(self) -> dict:
        return {
            "Empresa":           self.empresa,
            "Banco":             self.banco,
            "Saldo Actual":      self.saldo_actual,
            "Gastos del Día":    self.gastos_dia,
            "Intereses del Día": self.intereses_dia,
            "Cobros del Día":    self.cobros_dia,
            "Pagos del Día":     self.pagos_dia,
            "Movimientos":       self.movimientos_count,
        }


@dataclass
class CajaEntry:
    """Entrada para el archivo CAJA FÁBRICA DIGITAL."""

    dia: int = 0
    fecha: Optional[date] = None
    nro_tipo: Optional[int] = None
    tipo: str = ""
    importe: float = 0.0
    descripcion: str = ""
    canal: str = ""
    empresa: str = ""
    banco: str = ""

    def to_dict(self) -> dict:
        return {
            "DIA":         self.dia,
            "Fecha":       self.fecha,
            "NRO TIPO":    self.nro_tipo,
            "TIPO":        self.tipo,
            "IMPORTE":     self.importe,
            "DESCRIPCIÓN": self.descripcion,
            "Canal":       self.canal,
            "Empresa":     self.empresa,
            "Banco":       self.banco,
        }


@dataclass
class ProcessResult:
    """Resultado del procesamiento completo."""

    transactions: list = field(default_factory=list)
    summaries: list = field(default_factory=list)
    caja_entries: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    sheets_processed: int = 0
    transactions_total: int = 0

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def success(self) -> bool:
        return self.transactions_total > 0
