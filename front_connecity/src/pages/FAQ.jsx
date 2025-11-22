import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

export default function FAQ() {
  const navigate = useNavigate();

  const faqs = [
    {
      category: 'Uso Básico',
      questions: [
        {
          question: 'Como buscar uma rota?',
          answer: 'Na tela inicial, digite o local de origem e destino nos campos de busca. Selecione as opções que aparecerem na lista de sugestões. Depois, escolha seu perfil de mobilidade (Padrão, Idoso ou PcD) e clique em "Buscar Rotas".'
        },
        {
          question: 'Como salvar uma rota favorita?',
          answer: 'Após visualizar os detalhes de uma rota, clique no ícone de favorito (bookmark) no topo da tela. Dê um nome para a rota (ex: Casa, Trabalho) e escolha um ícone. A rota será salva e você poderá acessá-la na aba "Favoritos".'
        },
        {
          question: 'Como iniciar a navegação?',
          answer: 'Na tela de detalhes da rota, clique no botão "Iniciar Rota". O aplicativo pedirá permissão para usar sua localização. A navegação mostrará o mapa em tela cheia com instruções passo a passo baseadas na sua posição GPS.'
        }
      ]
    },
    {
      category: 'Perfis de Mobilidade',
      questions: [
        {
          question: 'Qual a diferença entre os perfis?',
          answer: 'O perfil "Padrão" é para usuários sem restrições de mobilidade. O perfil "Idoso" prioriza rotas com menos caminhada e mais tempo de espera. O perfil "PcD" evita barreiras como escadas, calçadas ruins e alagamentos, priorizando acessibilidade.'
        },
        {
          question: 'Como alterar meu perfil?',
          answer: 'Vá até a aba "Perfil" no menu inferior, depois em "Perfil de Mobilidade" e selecione o perfil desejado. As alterações são salvas automaticamente e serão usadas nas próximas buscas de rotas.'
        },
        {
          question: 'O perfil afeta as rotas sugeridas?',
          answer: 'Sim! O perfil selecionado influencia o cálculo das rotas. Por exemplo, o perfil PcD evita barreiras e prioriza acessibilidade, enquanto o perfil Idoso pode priorizar menos caminhada.'
        }
      ]
    },
    {
      category: 'Acessibilidade',
      questions: [
        {
          question: 'Como aumentar o tamanho da fonte?',
          answer: 'Vá até a aba "Perfil" > "Acessibilidade" e ative o toggle "Aumentar fonte". Isso aumentará o tamanho de todos os textos do aplicativo para facilitar a leitura.'
        },
        {
          question: 'O que é o modo alto contraste?',
          answer: 'O modo alto contraste aumenta a diferença entre cores do aplicativo, facilitando a visualização para pessoas com dificuldades visuais. Ative em "Perfil" > "Acessibilidade" > "Alto contraste".'
        },
        {
          question: 'Como reportar uma barreira?',
          answer: 'Durante a navegação ou na tela de detalhes da rota, clique em "Reportar Barreira". Selecione o tipo de barreira (escada, calçada ruim, alagamento, etc.), informe a localização e, se possível, anexe uma foto. Seu relato ajuda outros usuários!'
        }
      ]
    },
    {
      category: 'Navegação',
      questions: [
        {
          question: 'Como funciona a navegação em tempo real?',
          answer: 'A navegação usa o GPS do seu dispositivo para acompanhar sua posição. O aplicativo mostra qual passo você deve seguir e avança automaticamente conforme você se aproxima dos pontos da rota.'
        },
        {
          question: 'Posso ver ônibus em tempo real?',
          answer: 'Sim! Na tela de detalhes da rota, ative a opção "Mostrar ônibus em tempo real". Você verá a posição dos ônibus no mapa e previsões de chegada nas paradas.'
        },
        {
          question: 'O que fazer se perder a rota?',
          answer: 'O aplicativo recalcula automaticamente a rota baseado na sua posição atual. Se necessário, você pode voltar à tela de detalhes e reiniciar a navegação.'
        }
      ]
    },
    {
      category: 'Problemas e Soluções',
      questions: [
        {
          question: 'Não encontrei nenhuma rota. O que fazer?',
          answer: 'Verifique se selecionou origem e destino da lista de sugestões (não apenas digitou). Certifique-se de que os locais estão dentro da área de cobertura do sistema de transporte público.'
        },
        {
          question: 'A navegação não está funcionando. Por quê?',
          answer: 'Verifique se permitiu o acesso à localização do dispositivo. Vá nas configurações do navegador e permita o uso da localização para este site. Também verifique se o GPS está ativado no seu dispositivo.'
        },
        {
          question: 'Como atualizar os dados de transporte?',
          answer: 'Os dados são atualizados automaticamente pelo servidor. Se você notar informações desatualizadas, tente recarregar a página ou aguarde alguns minutos para a próxima atualização.'
        }
      ]
    }
  ];

  return (
    <div className="relative flex min-h-screen w-full flex-col justify-between overflow-x-hidden bg-white">
      <div className="flex-1">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-white border-b border-gray-200">
          <div className="flex items-center p-4">
            <button
              onClick={() => navigate(-1)}
              className="text-[var(--text-primary)]"
            >
              <span className="material-symbols-outlined">arrow_back_ios_new</span>
            </button>
            <h1 className="flex-1 text-center text-lg font-bold text-[var(--text-primary)]">
              Perguntas Frequentes
            </h1>
            <div className="w-8"></div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto pb-24 px-4 py-6">
          <p className="text-sm text-gray-600 mb-6">
            Encontre respostas para as dúvidas mais comuns sobre o uso do aplicativo.
          </p>

          {faqs.map((category, categoryIndex) => (
            <section key={categoryIndex} className="mb-8">
              <h2 className="text-base font-bold text-gray-900 mb-4">
                {category.category}
              </h2>
              <div className="space-y-4">
                {category.questions.map((faq, faqIndex) => (
                  <details
                    key={faqIndex}
                    className="group bg-gray-50 rounded-lg border border-gray-200 overflow-hidden"
                  >
                    <summary className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-100 transition-colors">
                      <span className="text-sm font-medium text-gray-900 pr-4">
                        {faq.question}
                      </span>
                      <span className="material-symbols-outlined text-gray-400 shrink-0 transition-transform group-open:rotate-180">
                        expand_more
                      </span>
                    </summary>
                    <div className="px-4 pb-4 pt-2">
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {faq.answer}
                      </p>
                    </div>
                  </details>
                ))}
              </div>
            </section>
          ))}

          {/* Seção de Contato */}
          <section className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="text-base font-bold text-gray-900 mb-2">
              Ainda tem dúvidas?
            </h3>
            <p className="text-sm text-gray-700 mb-4">
              Se não encontrou a resposta que procurava, entre em contato conosco através dos canais de suporte.
            </p>
            <button
              onClick={() => {
                // TODO: Implementar página de contato
                alert('Página de contato - Em desenvolvimento');
              }}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              Entrar em Contato
            </button>
          </section>
        </main>
      </div>

      {/* Footer com BottomNav */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <BottomNav />
        <div className="h-safe-area-bottom bg-white"></div>
      </footer>
    </div>
  );
}

