function fn() {
  // URL de la app desplegada. Se pasa desde Maven (-Dkarate.baseUrl=...).
  var baseUrl = karate.properties['karate.baseUrl'] || 'http://localhost:8000';
  karate.configure('connectTimeout', 5000);
  karate.configure('readTimeout', 10000);
  karate.configure('logPrettyResponse', true);
  return {
    baseUrl: baseUrl,
    // Genera SKUs únicos: la BD desplegada es compartida y no se limpia.
    uniqueSku: function (prefix) {
      return prefix + '-' + java.util.UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    }
  };
}
