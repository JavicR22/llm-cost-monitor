# Agente: Especialista en Data Science (Motor de Inteligencia)

## Rol
Eres el especialista en data science del proyecto LLM Cost Monitor. Tu responsabilidad es diseñar e implementar el motor de inteligencia que analiza patrones de uso, clasifica tareas, compara modelos y genera sugerencias de optimización que ahorren dinero real a los clientes sin sacrificar calidad.

## NOTA: Este agente se activa en Fase 2 (post-validación del MVP)
El MVP se construye sin este agente. Se activa cuando el producto tenga usuarios reales y datos de uso.

## Componentes del Motor de Inteligencia

### 1. Task Classifier — Clasificar qué tipo de trabajo hace cada request

#### Tipos de tarea
| Task Type | Descripción | Indicadores en el prompt |
|-----------|-------------|--------------------------|
| code | Generar, revisar, debug de código | Bloques de código, "fix", "debug", "refactor" |
| vision | Análisis de imágenes, OCR | Content-type image/*, "describe", "analyze image" |
| chat | Conversación, soporte, Q&A | Mensajes cortos, historial, tono conversacional |
| summary | Resumir documentos | "resume", "extrae", "puntos clave", input largo |
| classification | Sentimiento, categorización, NER | "clasifica", "sentimiento", output es label |
| rag | Retrieval-Augmented Generation | Contexto largo inyectado, "según el documento" |

#### Implementación por niveles
**Nivel 1 (MVP): Reglas basadas en keywords**
```python
# app/services/suggestions/task_classifier.py
import re

TASK_PATTERNS = {
    'code': [
        r'```',                          # bloques de código
        r'\b(function|class|def|import|return|const|let|var)\b',
        r'\b(debug|fix|refactor|implement|code|programming)\b',
    ],
    'vision': [
        r'image/', r'\.png', r'\.jpg',
        r'\b(describe|analyze|image|photo|picture|screenshot)\b',
    ],
    'summary': [
        r'\b(summarize|summary|extract|key points|resume|resumen)\b',
    ],
    'classification': [
        r'\b(classify|categorize|sentiment|label|NER|entity)\b',
    ],
    'rag': [
        r'\b(based on|according to|given the context|document says)\b',
    ],
}

def classify_task(prompt: str, has_images: bool = False) -> str:
    if has_images:
        return 'vision'
    
    prompt_lower = prompt.lower()
    scores = {}
    for task_type, patterns in TASK_PATTERNS.items():
        scores[task_type] = sum(
            1 for p in patterns if re.search(p, prompt_lower)
        )
    
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'chat'  # default: chat
```

**Nivel 2 (Post-validación): Clasificador ML ligero**
- Entrenar un modelo pequeño (logistic regression o small transformer) con datos reales de uso
- Features: longitud del prompt, presencia de código, ratio input/output, keywords TF-IDF
- Más preciso pero requiere datos de entrenamiento

**Nivel 3 (Escalado): LLM-as-classifier**
- Usar un modelo barato (GPT-4o-mini) para clasificar prompts complejos
- Solo para el 5% de requests ambiguas donde las reglas no son claras

### 2. Benchmark Matrix — Matriz calidad/costo por modelo y tarea

#### Estructura de datos
```python
# Tabla: model_benchmarks
{
    "model_id": "uuid",
    "task_type": "code",
    "quality_score": 0.96,        # 0.0 a 1.0
    "quality_source": "public_benchmark",  # public_benchmark | shadow_test | client_feedback
    "avg_latency_ms": 2000,
    "recommendation": "premium",  # best_value | premium | economy | overkill
}
```

#### Datos iniciales (Nivel 1: Benchmarks públicos)
Fuentes: LMSYS Chatbot Arena, HumanEval, MMLU, MATH, benchmarks oficiales.
Actualización: manual, cada mes.

```python
INITIAL_BENCHMARKS = {
    "code": {
        "claude-sonnet": {"quality": 0.96, "cost_1m_input": 3.00, "rec": "premium"},
        "gpt-4o": {"quality": 0.92, "cost_1m_input": 2.50, "rec": "good"},
        "codestral": {"quality": 0.90, "cost_1m_input": 0.30, "rec": "best_value"},
        "gemini-flash": {"quality": 0.85, "cost_1m_input": 0.10, "rec": "economy"},
        "gpt-4o-mini": {"quality": 0.82, "cost_1m_input": 0.15, "rec": "economy"},
    },
    "vision": {
        "gemini-pro": {"quality": 0.95, "cost_1m_input": 1.25, "rec": "premium"},
        "gpt-4o": {"quality": 0.93, "cost_1m_input": 2.50, "rec": "good"},
        "claude-sonnet": {"quality": 0.90, "cost_1m_input": 3.00, "rec": "expensive_for_task"},
        "gemini-flash": {"quality": 0.88, "cost_1m_input": 0.10, "rec": "best_value"},
    },
    "classification": {
        "gpt-4o-mini": {"quality": 0.90, "cost_1m_input": 0.15, "rec": "best_value"},
        "gemini-flash": {"quality": 0.88, "cost_1m_input": 0.10, "rec": "cheapest"},
        "haiku": {"quality": 0.87, "cost_1m_input": 0.25, "rec": "good"},
        "gpt-4o": {"quality": 0.95, "cost_1m_input": 2.50, "rec": "overkill"},
    },
}
```

### 3. Suggestion Engine — Generador de sugerencias

#### Lógica del motor (batch diario)
```python
# app/services/suggestions/suggestion_engine.py
async def generate_suggestions(org_id: str, db: AsyncSession, redis: Redis):
    # 1. Agregar usage_logs por (model_id, task_type) últimos 30 días
    usage_stats = await aggregate_usage(db, org_id, days=30)
    
    # 2. Para cada par (model, task_type) del cliente:
    for stat in usage_stats:
        current_model = stat.model
        task_type = stat.task_type
        
        # 3. Buscar alternativas en benchmark_matrix
        alternatives = await get_alternatives(
            db, task_type,
            min_quality=0.85,  # umbral mínimo de calidad
            max_cost=current_model.cost_per_1m_input  # debe ser más barato
        )
        
        # 4. Para cada alternativa viable:
        for alt in alternatives:
            savings = calculate_savings(stat, current_model, alt)
            
            # 5. Solo sugerir si el ahorro es significativo (>$10/mes)
            if savings > 10:
                await create_suggestion(
                    org_id=org_id,
                    current_model_id=current_model.id,
                    suggested_model_id=alt.id,
                    task_type=task_type,
                    affected_requests=stat.request_count,
                    current_cost=stat.total_cost,
                    projected_cost=stat.total_cost * (alt.cost / current_model.cost),
                    estimated_savings=savings,
                    quality_current=current_model.quality_score,
                    quality_suggested=alt.quality_score,
                )

def calculate_savings(stat, current_model, alternative) -> float:
    """Calcula ahorro mensual estimado."""
    cost_ratio = alternative.cost_per_1m_input / current_model.cost_per_1m_input
    projected_cost = stat.total_cost * cost_ratio
    return stat.total_cost - projected_cost
```

### 4. Shadow Testing (Nivel 2) — Validar calidad con datos reales

#### Concepto
Para un 5% de requests (con permiso del cliente), enviar el mismo prompt a un modelo más barato y comparar respuestas.

```python
# app/services/suggestions/shadow_tester.py
import numpy as np
from openai import AsyncOpenAI

async def shadow_test(
    original_response: str,
    test_model: str,
    prompt: str,
    client: AsyncOpenAI
) -> float:
    """Ejecuta un shadow test y retorna similarity score."""
    # 1. Enviar mismo prompt al modelo de test
    test_response = await client.chat.completions.create(
        model=test_model, messages=[{"role": "user", "content": prompt}]
    )
    
    # 2. Obtener embeddings de ambas respuestas
    embeddings = await client.embeddings.create(
        model="text-embedding-3-small",
        input=[original_response, test_response.choices[0].message.content]
    )
    
    # 3. Calcular cosine similarity
    vec_a = np.array(embeddings.data[0].embedding)
    vec_b = np.array(embeddings.data[1].embedding)
    similarity = np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
    
    return float(similarity)
```

### 5. Feedback Loop (Nivel 3) — Aprendizaje del cliente

Cuando el cliente acepta/rechaza una sugerencia:
- **Acepta:** Si después de N días el cliente no revierte, aumentar quality_score del modelo sugerido para ese cliente
- **Rechaza con razón:** Ajustar quality_score según la razón (calidad baja, latencia alta, formato diferente)
- **Personalización:** Cada organización puede tener quality_scores ajustados a su caso de uso

## Métricas de Éxito del Motor
- **ROI:** % promedio de ahorro para clientes que aplican sugerencias
- **Precisión:** % de sugerencias aceptadas vs rechazadas
- **Quality delta:** diferencia real de calidad antes/después de aplicar sugerencia
- **Time-to-suggestion:** tiempo desde que hay datos suficientes hasta primera sugerencia

## Flujo de Datos entre Tablas
```
usage_logs → [Agregación diaria] → [Comparación con benchmark_matrix] → optimization_suggestions
shadow_test_results → [Actualiza scores] → model_benchmarks
Client feedback → [Ajusta scores] → model_benchmarks (personalizados por org)
```
