# Directory structure and roles

- domain
  - role: contains the domain logic and interfaces to the external system.
  - example: order
- infrastructure
  - role: contains the implementation of the interfaces in the domain
  - example: database, external API like Binance
- application
  - role: coordinator between the external system and domain logic
  - example: Fetch market data from multiple exchanges and choose the best price by domain logic.
- interfaces
  - role: contains the interfaces to the external system
  - example: cli
