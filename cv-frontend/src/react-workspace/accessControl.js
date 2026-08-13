const INTERNAL_READ_ALL = new Set(['SUPER_ADMIN', 'DIRETOR', 'ENGENHARIA', 'AUDITOR']);

export const menuByRole = {
  SUPER_ADMIN: ['Tudo', 'Decisoes Globais', 'Portfolio Completo', 'Capital'],
  DIRETOR: ['Dashboard', 'Portfolio', 'Indicadores Macro', 'Simulacoes'],
  FINANCEIRO: ['DRE', 'Fluxo de Caixa', 'Investimentos', 'Pagamentos'],
  ENGENHARIA: ['Obras', 'Cronogramas', 'Performance'],
  QUALIDADE: ['Processos', 'Auditorias', 'Nao Conformidades'],
  AUDITOR: ['Saude', 'Riscos', 'Falhas'],
  GERENTE: ['Obra', 'Equipe', 'Tarefas'],
  FORNECEDOR: ['Pedidos', 'Contratos', 'Demandas'],
  CLIENTE: ['Meu Projeto', 'Status', 'Documentos'],
  COLABORADOR: ['Treinamentos', 'Tarefas Atribuidas'],
};

export function getMenuByRole(user) {
  const role = String(user?.role || 'COLABORADOR').toUpperCase();
  return menuByRole[role] || menuByRole.COLABORADOR;
}

export function canViewCard(user, card) {
  const role = String(user?.role || 'COLABORADOR').toUpperCase();
  const userId = user?.id;

  if (INTERNAL_READ_ALL.has(role)) return true;
  if (role === 'FORNECEDOR') return card?.owner_id === userId;
  if (role === 'QUALIDADE') return card?.stage === 'juridico' || card?.stage === 'proposal';
  if (role === 'FINANCEIRO') return card?.stage === 'closed';
  if (role === 'GERENTE' || role === 'CLIENTE' || role === 'COLABORADOR') return card?.owner_id === userId;

  return false;
}

export function canManageWorkspace(user) {
  const role = String(user?.role || 'COLABORADOR').toUpperCase();
  return role === 'SUPER_ADMIN' || role === 'DIRETOR' || role === 'ENGENHARIA';
}
