package tienda;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.intuit.karate.Results;
import com.intuit.karate.Runner;
import org.junit.jupiter.api.Test;

/** Ejecuta todos los .feature del paquete en paralelo y falla el build si alguno falla. */
class TiendaApiTest {

    @Test
    void testAll() {
        Results results = Runner.path("classpath:tienda")
                .tags("~@ignore")
                .outputJunitXml(true)
                .parallel(4);
        assertEquals(0, results.getFailCount(), results.getErrorMessages());
    }
}
