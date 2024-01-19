from flask import Blueprint
from flask_restx import Api, Resource, fields
from models.db_models import Estimacion
import numpy
import pickle

es = Blueprint('estimacion',__name__)

api = Api(
    es, 
    version='1.0', title='API REST',
    description='API REST entregable 3 Daniel Terron',
)

observacion_repr = api.model('Observacion', {
    'sepal_length': fields.Float(description="Longitud del sépalo"),
    'sepal_width': fields.Float(description="Anchura del sépalo"),
    'petal_length': fields.Float(description="Longitud del pétalo"),
    'petal_width': fields.Float(description="Anchura del pétalo"),
})


ns = api.namespace('entregable3', description='entregable3')
predictive_model = pickle.load(open('simple_model.pkl','rb'))

@es.route('/', methods=['GET', 'POST'])
class EstimacionListAPI(Resource):
    """ Manejador del listado de predicciones.
        GET devuelve la lista de predicciones históricas
        POST agrega una nueva predicción a la lista de predicciones
    """

    # -----------------------------------------------------------------------------------
    def get(self):
        """ Maneja la solicitud GET del listado de predicciones
        """
        return [
            marshall_prediction(prediction) for prediction in Estimacion.query.all()
        ], 200

    # -----------------------------------------------------------------------------------
    # La siguiente línea de código sirve para asegurar que el método POST recibe un
    # recurso representado por la observación descrita arriba (observacion_repr).
    @ns.expect(observacion_repr)
    def post(self):
        from app import db
        """ Procesa un nuevo recurso para que se agregue a la lista de predicciones
        """
        
        # La siguiente línea convierte una representación REST de una Prediccion en
        # un Objeto Prediccion mapeado en la base de datos mediante SQL Alchemy
        prediction = Estimacion(representation=api.payload)

        # Crea una observación para alimentar el modelo predicitivo, usando los
        # datos de entrada del API.
        model_data = [numpy.array([
            prediction.sepal_length, prediction.sepal_width, 
            prediction.petal_length, prediction.petal_width, 
        ])]
        prediction.predicted_tipo = str(predictive_model.predict(model_data)[0])
        print(prediction.predicted_tipo)
        # ---------------------------------------------------------------------

        # Las siguientes dos líneas de código insertan la predicción a la base
        # de datos mediante la biblioteca SQL Alchemy.
        db.session.add(prediction)
        db.session.commit()

        # Formar la respuesta de la predicción del modelo
        response_url = es.url_for(PredictionAPI, prediction_id=prediction.prediction_id)
        response = {
            "class": prediction.predicted_class,  # la clase que predijo el modelo
            "url": f'{api.base_url[:-1]}{response_url}',  # el URL de esta predicción
            "api_id": prediction.prediction_id  # El identificador de la base de datos
        }
        # La siguiente línea devuelve la respuesta a la solicitud POST con los datos
        # de la nueva predicción, acompañados del código HTTP 201: Created
        return response, 201


# =======================================================================================
# La siguiente línea de código maneja las solicitudes GET del listado de predicciones 
# acompañadas de un identificador de predicción, para obtener los datos de una particular
# Si el API permite modificar predicciones particulares, aquí se debería de manejar el
# método PUT o PATCH para una predicción en particular.
@ns.route('/<int:prediction_id>', methods=['GET'])
class PredictionAPI(Resource):
    """ Manejador de una predicción particular
    """

    # -----------------------------------------------------------------------------------
    @ns.doc({'prediction_id': 'Identificador de la predicción'})
    def get(self, prediction_id):
        """ Procesa las solicitudes GET de una predicción particular
            :param prediction_id: El identificador de la predicción a buscar
        """

        # Usamos la clase Prediction que mapea la tabla en la base de datos para buscar
        # la predicción que tiene el identificador que se usó como parámetro de esta
        # solicitud. Si no existe entonces se devuelve un mensaje de error 404 No encontrado
        prediction = Estimacion.query.filter_by(prediction_id=prediction_id).first()
        if not prediction:
            return 'Id {} no existe en la base de datos'.format(prediction_id), 404
        else:
            # Se usa la función "marshall_prediction" para convertir la predicción de la
            # base de datos a un recurso REST
            return marshall_prediction(prediction), 200


# =======================================================================================
def marshall_prediction(prediction):
    """ Función utilería para transofmrar una Predicción de la base de datos a una 
        representación de un recurso REST.
        :param prediction: La predicción a transformar
    """
    response_url = api.url_for(PredictionAPI, prediction_id=prediction.prediction_id)
    model_data = {
        'sepal_length': prediction.sepal_length,
        'sepal_width': prediction.sepal_width,
        'petal_length': prediction.petal_length,
        'petal_width': prediction.petal_width,
        "class": str(prediction.predicted_class)
    }
    response = {
        "api_id": prediction.prediction_id,
        "url": f'{api.base_url[:-1]}{response_url}',
        "created_date": prediction.created_date.isoformat(),
        "prediction": model_data
    }
    return response

