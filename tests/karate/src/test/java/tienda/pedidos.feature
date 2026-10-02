Feature: API de pedidos (reglas de negocio vistas desde afuera)

  Background:
    * url baseUrl

  Scenario Outline: cliente <cliente> compra <cantidad> x S/ <precio>
    # Data-driven: una tabla de casos de negocio, legible por QA y negocio
    * call read('common/crear-producto.feature') { price: '<precio>', stock: 10 }
    Given path 'orders'
    And request { customer_type: '<cliente>', items: [{ sku: '#(producto.sku)', quantity: <cantidad> }] }
    When method post
    Then status 201
    And match response ==
      """
      {
        id: '#number',
        subtotal: '<subtotal>',
        discount: '<descuento>',
        igv: '<igv>',
        total: '<total>',
        payment_id: '#regex pay_[0-9a-f]{12}'
      }
      """

    Examples:
      | cliente   | precio | cantidad | subtotal | descuento | igv    | total   |
      | REGULAR   | 100.00 | 1        | 100.00   | 0.00      | 18.00  | 118.00  |
      | FRECUENTE | 100.00 | 2        | 200.00   | 10.00     | 34.20  | 224.20  |
      | VIP       | 100.00 | 3        | 300.00   | 30.00     | 48.60  | 318.60  |
      | REGULAR   | 250.00 | 2        | 500.00   | 25.00     | 85.50  | 560.50  |
      | VIP       | 300.00 | 2        | 600.00   | 90.00     | 91.80  | 601.80  |

  Scenario: un pedido exitoso descuenta stock
    * call read('common/crear-producto.feature') { stock: 5 }
    Given path 'orders'
    And request { items: [{ sku: '#(producto.sku)', quantity: 2 }] }
    When method post
    Then status 201

    Given path 'products', producto.sku
    When method get
    Then status 200
    And match response.stock == 3

  Scenario: stock insuficiente devuelve 409 y no altera el stock
    * call read('common/crear-producto.feature') { stock: 1 }
    Given path 'orders'
    And request { items: [{ sku: '#(producto.sku)', quantity: 5 }] }
    When method post
    Then status 409
    And match response.detail contains 'Stock insuficiente'

    Given path 'products', producto.sku
    When method get
    Then match response.stock == 1

  Scenario: pago rechazado devuelve 402 y no altera el stock
    # 2 x 6000 + IGV supera PAYMENT_LIMIT=10000 de la pasarela simulada
    * call read('common/crear-producto.feature') { price: '6000.00', stock: 3 }
    Given path 'orders'
    And request { items: [{ sku: '#(producto.sku)', quantity: 2 }] }
    When method post
    Then status 402

    Given path 'products', producto.sku
    When method get
    Then match response.stock == 3

  Scenario: tipo de cliente inválido devuelve 422
    * call read('common/crear-producto.feature')
    Given path 'orders'
    And request { customer_type: 'PLATINUM', items: [{ sku: '#(producto.sku)', quantity: 1 }] }
    When method post
    Then status 422
