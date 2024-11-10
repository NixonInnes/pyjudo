# PyJudo

## Overview
**PyJudo** is a python library to support the [dependency injection](https://en.wikipedia.org/wiki/Dependency_injection) (DI) pattern. . It facilitates the registration of services, resolves dependencies, and manages the lifecycle of services throughout your application. By decoupling service creation from business logic, PyJudo promotes cleaner, more maintainable, and testable codebases.

## Installation
PyJudo is available on PyPi; install using:
```bash
pip install pyjudo
```


## Features
- Service lifetimes:
  - Singletons: A single instance created and  shared across the application
  - Scoped: A single instance created and shared within a scope
  - Transient: A new instance is created every time the service is requested.

- Disposable services:
  - Automatically disposes of services that implement the `IDisposable` protocol when a scope ends.

- Circular dependencies:
  - Detects and prevents circular dependencies during service resolution.

- Thread safety:
  - Ensures safe use in multi-threaded environments by managing scopes and service resolutions per thread.

- Context management
  - Supports the use of context managers (i.e. `with ...`) to manage service scopes and their respective service lifetimes.

## Quick Start

### 1. Define Interfaces and Implementations
Start by defining service interfaces (abstract classes) and their concrete implementations:

```python
from abc import ABC, abstractmethod
from pyjudo import ServiceContainer, ServiceLife

# Define service interfaces
class IDatabaseConnection(ABC):
    @abstractmethod
    def query(self, sql: str) -> Any: ...

class IDatabaseURIBuilder(ABC):
    @abstractmethod
    def get_uri(self) -> str: ...


# Implement the services
class DatabaseConnection(IDatabaseConnection):
    def __init__(self, uri_builder: IDatabaseURIBuilder, table_name="default"):
        self.connection_string = uri_builder.get_uri()
        self.table_name = table_name
        self.connected = True
        print(f"Connected to database: {self.connection_string}")

    def query(self, sql: str) -> Any:
        if not self.connected:
            raise Exception("Not connected to the database.")
        print(f"Executing query: {sql} FROM {self.table_name}")
        return {"result": "data"}

    def dispose(self) -> None:
        if self.connected:
            self.connected = False
            print(f"Disconnected from database: {self.connection_string}")

class TestDatabaseURIBuilder(IDatabaseURIBuilder):
    def get_uri(self):
        return "connect.to.me"
```

### 2. Register Services
Create an instance of the `ServiceContainer` and register your services with appropriate lifetimes:

```python
# Create the service container
services = ServiceContainer()

# Register services
services.add_transient(IDatabaseURIBuilder, TestDatabaseURIBuilder)
services.add_scoped(IDatabaseConnection, DatabaseConnection)
```

### 3. Resolve Services
Retrieve and utilise services from the `ServiceCollection`. When retrieving services from the `ServiceContainer`, services referenced in constructors (`__init__`) will be automatically resolved.  
You can also overwrite any constructor arguments when retrieving services:
```python
with services.create_scope() as service_scope:
    db = service_scope[IDatabaseConnection](table_name="foobar")
    result = db.query("SELECT *")
    print(result)

# Output:
# "Connected to database: connect.to.me"
# "Executing query: SELECT * on foobar"
# "Disconnected from database: connect.to.me"
```
> NOTE: PyJudo will automatically "dispose" scoped services which implement `IDisposable` (i.e. have a `dispose()` method) by calling `dispose()` on them when the service scope exits.