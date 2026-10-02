Feature: API de productos

  Background:
    * url baseUrl
    # Esquema esperado de un producto: marcadores "fuzzy" de Karate
    * def productoSchema = { id: '#number', sku: '#string', name: '#string', price: '#regex \\d+\\.\\d{2}', stock: '#number? _ >= 0' }

  Scenario: health check
    Given path 'health'
    When method get
    Then status 200
    And match response == { status: 'ok' }

  Scenario: crear un producto y consultarlo por SKU
    * def sku = uniqueSku('PRD')
    Given path 'products'
    And request { sku: '#(sku)', name: 'Teclado mecánico', price: '249.90', stock: 7 }
    When method post
    Then status 201
    And match response == productoSchema
    And match response contains { sku: '#(sku)', price: '249.90', stock: 7 }

    Given path 'products', sku
    When method get
    Then status 200
    And match response.name == 'Teclado mecánico'

  Scenario: el listado devuelve productos que cumplen el esquema
    * call read('common/crear-producto.feature')
    Given path 'products'
    When method get
    Then status 200
    And match each response == productoSchema
    And match response[*].sku contains producto.sku

  Scenario: SKU duplicado devuelve 409
    * def creado = call read('common/crear-producto.feature')
    Given path 'products'
    And request { sku: '#(creado.producto.sku)', name: 'Otro', price: '1.00', stock: 1 }
    When method post
    Then status 409
    And match response.detail contains 'ya existe'

  Scenario: producto inexistente devuelve 404
    Given path 'products', 'NO-EXISTE-' + java.lang.System.currentTimeMillis()
    When method get
    Then status 404

  Scenario Outline: validación de entrada rechaza <caso>
    Given path 'products'
    And request <body>
    When method post
    Then status 422

    Examples:
      | caso              | body                                                    |
      | precio negativo   | { sku: 'X1', name: 'X', price: '-5', stock: 1 }         |
      | stock negativo    | { sku: 'X2', name: 'X', price: '5.00', stock: -1 }      |
      | SKU vacío         | { sku: '', name: 'X', price: '5.00', stock: 1 }         |
      | falta el nombre   | { sku: 'X3', price: '5.00', stock: 1 }                  |
