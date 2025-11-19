import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

export default function FAQ() {
  const navigate = useNavigate();
  
  // Perguntas frequentes mockadas
  const [faqs] = useState([
    {
      id: 1,
      question: 'Como calcular uma rota?',
      answer: 'Para calcular uma rota, preencha os campos de origem e destino na tela inicial, selecione seu perfil de mobilidade (Padrão, Idoso ou PcD) e clique em "Buscar Rota". O sistema irá apresentar as melhores opções de rota considerando suas preferências de acessibilidade.'
    },
    {
      id: 2,
      question: 'Quais perfis de mobilidade estão disponíveis?',
      answer: 'O sistema oferece três perfis de mobilidade: Padrão (para usuários sem necessidades especiais), Idoso (otimizado para pessoas idosas com preferência por menos caminhadas) e PcD (Pessoa com Deficiência, com foco em acessibilidade completa, evitando escadas e calçadas ruins).'
    },
    {
      id: 3,
      question: 'Como salvar uma rota favorita?',
      answer: 'Após visualizar os detalhes de uma rota, você pode salvá-la como favorita clicando no ícone de estrela ou no botão "Salvar como Favorito". As rotas favoritas ficam disponíveis na aba "Favoritos" para acesso rápido.'
    },
    {
      id: 4,
      question: 'O sistema funciona offline?',
      answer: 'Sim! O sistema permite salvar rotas para uso offline. As rotas salvas ficam disponíveis mesmo sem conexão com a internet, permitindo que você acesse suas rotas favoritas a qualquer momento.'
    },
    {
      id: 5,
      question: 'Como ajustar as preferências de rota?',
      answer: 'Acesse a página de Configurações através do menu Perfil. Lá você pode ajustar preferências como "Prefiro andar menos" e "Prefiro menos transferências" usando os sliders, além de configurar opções de acessibilidade como fonte grande e alto contraste.'
    },
    {
      id: 6,
      question: 'O sistema mostra ônibus em tempo real?',
      answer: 'Sim! O sistema integra dados em tempo real da SPTrans através da API Olho Vivo. Você pode ativar a visualização de ônibus em tempo real na tela inicial ou nos detalhes da rota para ver a posição atual dos veículos e previsões de chegada nas paradas.'
    },
    {
      id: 7,
      question: 'Como funciona a busca de rotas?',
      answer: 'O sistema utiliza algoritmos de grafos (Dijkstra e Yen) para calcular as melhores rotas considerando tempo, custo, acessibilidade e suas preferências pessoais. As rotas são calculadas em tempo real com base nos dados de transporte público e infraestrutura urbana.'
    },
    {
      id: 8,
      question: 'Posso usar o sistema em outras cidades?',
      answer: 'Atualmente, o sistema está otimizado para a cidade de São Paulo, utilizando dados da SPTrans e infraestrutura local. Futuramente, planejamos expandir para outras cidades brasileiras.'
    },
    {
      id: 9,
      question: 'Como reportar um problema ou erro?',
      answer: 'Se encontrar algum problema ou erro no sistema, você pode entrar em contato através da seção "Ajuda e Suporte" na página de Perfil. Nossa equipe está sempre pronta para ajudar e melhorar o sistema com base no seu feedback.'
    },
    {
      id: 10,
      question: 'O sistema é gratuito?',
      answer: 'Sim! O Conneccity é totalmente gratuito e foi desenvolvido como um projeto acadêmico focado em acessibilidade e inclusão no transporte público. Não há custos ou assinaturas para usar o sistema.'
    }
  ]);

  const [openFaq, setOpenFaq] = useState(null);

  const toggleFaq = (id) => {
    setOpenFaq(openFaq === id ? null : id);
  };

  return (
    <div className="min-h-screen bg-white pb-24">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="flex items-center p-4">
          <button 
            onClick={() => navigate(-1)}
            className="p-2 -ml-2 text-gray-600 hover:bg-gray-100 rounded-full"
          >
            <span className="material-symbols-outlined text-2xl">arrow_back</span>
          </button>
          <h1 className="flex-1 text-center text-lg font-semibold text-gray-900 -mr-10">
            Perguntas Frequentes
          </h1>
        </div>
      </header>

      <main className="px-4 py-6">
        {/* Introdução */}
        <div className="mb-6">
          <p className="text-sm text-gray-600">
            Encontre respostas para as dúvidas mais comuns sobre o Conneccity. 
            Se não encontrar o que procura, entre em contato conosco através da seção de suporte.
          </p>
        </div>

        {/* Lista de FAQs */}
        <div className="space-y-3">
          {faqs.map((faq) => (
            <div
              key={faq.id}
              className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm"
            >
              {/* Pergunta */}
              <button
                onClick={() => toggleFaq(faq.id)}
                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
              >
                <span className="flex-1 text-sm font-semibold text-gray-900 pr-4">
                  {faq.question}
                </span>
                <span
                  className={`material-symbols-outlined text-gray-400 transition-transform flex-shrink-0 ${
                    openFaq === faq.id ? 'rotate-180' : ''
                  }`}
                >
                  expand_more
                </span>
              </button>

              {/* Resposta */}
              {openFaq === faq.id && (
                <div className="px-4 pb-4 border-t border-gray-100">
                  <p className="pt-4 text-sm text-gray-600 leading-relaxed">
                    {faq.answer}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Seção de Contato */}
        <div className="mt-8 p-6 bg-primary-50 rounded-2xl border border-primary-100">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary-600 text-2xl">support_agent</span>
            </div>
            <div className="flex-1">
              <h3 className="text-base font-bold text-gray-900 mb-2">
                Ainda precisa de ajuda?
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Nossa equipe de suporte está pronta para ajudar você. Entre em contato conosco.
              </p>
              <button className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors">
                Entrar em Contato
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <BottomNav />
      </div>
    </div>
  );
}


