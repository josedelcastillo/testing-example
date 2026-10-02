@ignore
Feature: Helper reutilizable para crear un producto (se invoca con `call`)

  Scenario:
    * def body =
      """
      {
        sku: '#(uniqueSku("KRT"))',
        name: '#(karate.get("name", "Producto Karate"))',
        price: '#(karate.get("price", "100.00"))',
        stock: '#(karate.get("stock", 10))'
      }
      """
    Given url baseUrl
    And path 'products'
    And request body
    When method post
    Then status 201
    * def producto = response
