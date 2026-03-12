"""
Set required environment variables before any app imports.
These are test-only values — never use in production.
"""
import os

_PRIVATE_KEY = (
    "-----BEGIN RSA PRIVATE KEY-----\\nMIIEpAIBAAKCAQEAwXuXTguO0SNZ3t9VFnC9KztTiJ2Zgik9bRJUKDXFOC5COMEn"
    "\\nYrDxgg+gafn+MvPexI4SDXsAWUPYL9qxzLn7E9ywsA8PKeK3jCB59Ihhe820Q+t1"
    "\\nuRqG/+dlse9zy82dNaaac4jM7msV/sRBUJvzIgaeinZYF4JDsDArYA4EdVK84WDy"
    "\\nh58gTi73PhJHdEd0J6KKevgE7hm66JGa9YtC/zra+CbQU9LtzJG/W4mySrm/qB2H"
    "\\nkxPjVS12jyBIEl/rnd0Bn4Afa99FjgJ+21+D3HqbTBeib3TLJ3dmXpR/0It0Xcnf"
    "\\nDLG13BRrdGFV6daHLVCVU/YkqfXs2PhBfWGPMwIDAQABAoIBAE95nOUKClgN1VSf"
    "\\nGCxnksy3SdDMK8ozdm/fH4KE08YH+lulu6/mTs3F7Xaaobf8RH0ofnHbHIGORLcj"
    "\\ndfVKT8AQ3uLyzJ+/6PU+QdoYSzK3hFyB05F9PAbR3gwA9+e3ReRL0xWyE7u7cQV9"
    "\\nR/b8mBpZ7bWidvzxHSy6HJcQKvSlmOmQd/L4b9UyNep1k/EQ9lgX3tMvhlIebcBR"
    "\\nP1dEXLRDX8qAvDOGyiWUPW9m2Lzjn3K0Cfz3HuIQqgrpeNpjGpU//tirIUAPyy/R"
    "\\nerO3xvaqwqn8/9f0fHo5d125rKqvkRud6fov4KBFE92X84AmZ2c0uaiuW/2pj4sc"
    "\\n6PNRK8ECgYEA31XQbyZebRexT1FLnWWWwRFoXdASPzKS/HRUC+bJ4tNC2F0Cb4/4"
    "\\nVd+1ZGHW8xHGq87j5IcReC2xpo0SY/PqUgj326iY5v5cm6QXbiraf4tOMqHjDuwZ"
    "\\nGUvfudPPf5bo7jXcdVCGvP/aR8H40KkfzKggvwaXeNNPcUMvwuFcieUCgYEA3cgI"
    "\\nZYZf8O8cZk1I7HxY1f8KaILlh6NJ4iVvFp9X0ZjVqSjK/+DPlZnzrrOqmvliL2eI"
    "\\nVQ7jzIWYdGCCQOWEFVsgwQDtNlflADBlwPy5toE856sylK7oxqOegX1yNMDIrcMO"
    "\\n6O9tIfDKMMG9VhV72VqyTSjaQJt8SVRj9TY1QzcCgYEAo9Jlz3J8p1dOx9jhN3aS"
    "\\na9LiFJaRG+x0J10JXaWQB6NiECXBqKYZypwLibO/IZOzgMmFH1f4d4hFHN+0Ur9T"
    "\\n7ZMIhQcaCa8hrUVjrnsexZog5UEcthB3pLekR8JYHcZL3JiDu0YzX6XpruNZKW41"
    "\\nlkDprFYgfA+84V8gRLpc0AUCgYBI80Q3yOSEBtLLn75N83TxJwwQZoYDgKWL2o5Y"
    "\\n3Z7wVZpqIv3q/tKpPdOW8og6o681MpP4joZFvufv19Lgb95re+chNSHRz0WHM2Q0"
    "\\n/6xCqO4Usg5YM9RjimxX4aCQU51u8otT+XVnRaHsOb4Cs9xiGWAu2zI3MC3InRao"
    "\\nEOWiLwKBgQDSY/Kj/uXwWFj10BpigY9dhiM31tS92DPlkSdBMkOaPa/ZIVG4oTlJ"
    "\\nJnqcmjb3mTpUY3RixTs485RtyCD/+c7cDQFPPHCaAjh/ETg+aqbP09vTXG+UZRKI"
    "\\noLUFuxyuW89N/47CMjY4CqSAGNqi7W77XYFbYE/knhuxo/m6r/xMSQ==\\n-----END RSA PRIVATE KEY-----\\n"
)

_PUBLIC_KEY = (
    "-----BEGIN PUBLIC KEY-----\\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwXuXTguO0SNZ3t9VFnC9"
    "\\nKztTiJ2Zgik9bRJUKDXFOC5COMEnYrDxgg+gafn+MvPexI4SDXsAWUPYL9qxzLn7"
    "\\nE9ywsA8PKeK3jCB59Ihhe820Q+t1uRqG/+dlse9zy82dNaaac4jM7msV/sRBUJvz"
    "\\nIgaeinZYF4JDsDArYA4EdVK84WDyh58gTi73PhJHdEd0J6KKevgE7hm66JGa9YtC"
    "\\n/zra+CbQU9LtzJG/W4mySrm/qB2HkxPjVS12jyBIEl/rnd0Bn4Afa99FjgJ+21+D"
    "\\n3HqbTBeib3TLJ3dmXpR/0It0XcnfDLG13BRrdGFV6daHLVCVU/YkqfXs2PhBfWGP"
    "\\nMwIDAQAB\\n-----END PUBLIC KEY-----\\n"
)

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://llmcost:llmcost@localhost:5432/llmcost")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("MASTER_ENCRYPTION_KEY", "V4hg3c-dnfDUiJPbLE7-AnDXshC6cIsf7ebnxsKaPec=")
os.environ.setdefault("JWT_PRIVATE_KEY", _PRIVATE_KEY)
os.environ.setdefault("JWT_PUBLIC_KEY", _PUBLIC_KEY)
