from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "LICEU 6.0 CORE-OS"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"

    JWT_SECRET_KEY: str = "sua_chave_mestra_secreta_aqui"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = "postgresql://user:password@postgres-csc:5432/holding_db"
    REDIS_URL: str = "redis://redis-liceu:6379/0"
    NATS_URL: str = "nats://nats:4222"
    NATS_CONNECT_TIMEOUT_SECONDS: float = 1.0
    EVENT_BUS_PROVIDER: str = "redis"
    KAFKA_BOOTSTRAP_SERVERS: str = ""
    CIVILIZATION_SENSOR_TOPIC: str = "civilization.sensor.stream"

    NEO4J_URI: str = ""
    NEO4J_USER: str = ""
    NEO4J_PASSWORD: str = ""
    POSTGIS_DSN: str = ""
    CESIUM_ION_ASSET_ID: str = ""

    ECONO_TOKEN_KEY: str = "chave_de_blindagem_econo_tech"
    LICEU_CURRENCY_SYMBOL: str = "LC$"

    URL_CEFEIDA: str = "http://cefeida:8000"
    URL_PD_IA: str = "http://pd-ia:8000"
    URL_BIM_ARQ: str = "http://bim-arq:8000"
    URL_CDVIRTUAL: str = "http://cdvirtual:8000"
    URL_FORNECEDORES: str = "http://fornecedores:8000"
    URL_GTAMKT: str = "http://gtamkt:8000"
    URL_ARCHIMEDES: str = "http://archimedes:8000"
    URL_CEA_INVEST: str = "http://cea-invest:8000"
    URL_INVEST_TECH: str = "http://invest-tech:8000"
    URL_INVESTOR_RELATIONS: str = "http://investor-relations:8080"
    URL_QUANT_ENGINE: str = "http://quant-engine:8082"
    URL_LICEU_EXCHANGE: str = "http://liceu-exchange:8083"
    URL_DECISION_INTELLIGENCE: str = "http://decision-intelligence:8084"
    URL_REVENUE_ENGINE: str = "http://revenue-engine:8085"
    URL_EXECUTION_ENGINE: str = "http://execution-engine:8086"
    URL_CAPITAL_ENGINE: str = "http://capital-engine:8087"
    URL_TRUST_LAYER: str = "http://trust-layer:8088"
    URL_ECONO_TECH: str = "http://econo-tech:8000"
    URL_PD_ENGINE: str = "http://pd-engine:8090"
    URL_BACKOFFICE: str = "http://backoffice:8000"
    URL_JURIDICO: str = "http://juridico-tech:8000"
    URL_ACADEMIA: str = "http://academia:8000"
    URL_OPERA: str = "http://opera:8000"
    URL_ANCHOR: str = "http://anchor:8000"
    URL_JOHN_LOCAL: str = "http://john-local:8000"
    OPERA_TIMEOUT_SECONDS: float = 1.5
    CANONICAL_EVENT_STORE_API_SECRET: str = ""
    CANONICAL_API_ENABLED: bool = False
    CANONICAL_API_TIMEOUT: float = 20.0

    DOMAIN_LICEU: str = "liceu60.com.br"
    DOMAIN_ARCHIMEDES: str = "archimedes.com.br"
    DOMAIN_CEFEIDA: str = "cefeida.ai"
    DOMAIN_ACADEMIA: str = "academia.liceu60.com.br"

    LOG_LEVEL: str = "info"
    HEALTH_CHECK_INTERVAL: int = 15

    NETWORK_NAME: str = "liceu-net"
    GATEWAY_PREFIX: str = "/gateway"
    JOH_EVENT_CHANNEL: str = "joh.brasileiro.eventos"
    ACADEMIA_EVENT_CHANNEL: str = "academia.saber.treinamentos"
    JOHN_TELEMETRY_CHANNEL: str = "john.brasileiro.telemetria"
    KANBAN_EVENT_CHANNEL: str = "kanban.updated"
    KANBAN_RUNTIME_REDIS_URL: str = "redis://localhost:6380/0"
    KANBAN_RUNTIME_EVENT_STREAM: str = "liceu.runtime.events"
    KANBAN_RUNTIME_SYNC_BATCH: int = 100
    JOHN_MEMORY_TTL_SECONDS: int = 3600
    JOHN_INTERNAL_TOKEN: str = "john-internal-dev"
    PUBLIC_PROXY_ENTRYPOINT: str = "http://localhost:8080"
    CRM_SCORING_MODEL_PATH: str = "relatorios_storage/crm_scoring_model.json"

    WHATSAPP_ENABLED: bool = False
    WHATSAPP_GRAPH_VERSION: str = "v20.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "liceu-john-whatsapp"
    WHATSAPP_DEFAULT_COUNTRY_CODE: str = "55"
    WHATSAPP_BUSINESS_NUMBER: str = "5511977601855"

    @property
    def PROJECT_NAME(self) -> str:
        return self.APP_NAME

    @property
    def SSO_SECRET_KEY(self) -> str:
        return self.JWT_SECRET_KEY

    @property
    def SSO_TOKEN_TTL_MINUTES(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
