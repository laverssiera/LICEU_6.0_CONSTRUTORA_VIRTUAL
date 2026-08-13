import api from './api';

export default {
  // Lista todas as obras da Irmandade (GET /obras)
  getObras() {
    return api.get('/obras');
  },

  // Cadastra um novo sonho (POST /obras)
  cadastrarObra(dadosObra) {
    return api.post('/obras', dadosObra);
  },

  // Busca detalhes de uma obra específica (Ex: para o ConcreteVision)
  getObraDetalhe(id) {
    return api.get(`/obras/${id}`);
  }
};
