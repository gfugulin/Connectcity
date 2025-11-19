import { useState } from 'react';

export default function ReportBarrier({ isOpen, onClose, onReport }) {
  const [tipoBarreira, setTipoBarreira] = useState('');
  const [localizacao, setLocalizacao] = useState('');
  const [observacoes, setObservacoes] = useState('');
  const [foto, setFoto] = useState(null);
  const [fotoPreview, setFotoPreview] = useState(null);

  const tiposBarreira = [
    'Escada sem rampa',
    'Calçada quebrada',
    'Ausência de calçada',
    'Obstáculo no caminho',
    'Sem sinalização tátil',
    'Rampa muito íngreme',
    'Outro'
  ];

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        alert('Arquivo muito grande. Máximo 10MB.');
        return;
      }
      setFoto(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setFotoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleFileChange({ target: { files: [file] } });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!tipoBarreira) {
      alert('Por favor, selecione um tipo de barreira.');
      return;
    }

    const reporte = {
      tipo: tipoBarreira,
      localizacao: localizacao || 'Localização não especificada',
      observacoes,
      foto: fotoPreview,
      timestamp: new Date().toISOString()
    };

    if (onReport) {
      onReport(reporte);
    }

    // Reset form
    setTipoBarreira('');
    setLocalizacao('');
    setObservacoes('');
    setFoto(null);
    setFotoPreview(null);
    onClose();
    
    alert('Barreira reportada com sucesso! Obrigado por ajudar outros usuários.');
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900">Reportar Barreira</h2>
            <p className="mt-1 text-sm text-gray-600">
              Descreva o impedimento para ajudar outros usuários.
            </p>
          </div>
          <button
            onClick={onClose}
            className="ml-4 text-gray-400 hover:text-gray-600"
          >
            <span className="material-symbols-outlined text-2xl">close</span>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Tipo de Barreira */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tipo de barreira
            </label>
            <select
              value={tipoBarreira}
              onChange={(e) => setTipoBarreira(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              required
            >
              <option value="">Selecione um tipo</option>
              {tiposBarreira.map((tipo) => (
                <option key={tipo} value={tipo}>
                  {tipo}
                </option>
              ))}
            </select>
          </div>

          {/* Localização Precisa */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Localização precisa
            </label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                location_on
              </span>
              <input
                type="text"
                value={localizacao}
                onChange={(e) => setLocalizacao(e.target.value)}
                placeholder="Ex: Em frente ao nº 123"
                className="w-full rounded-lg border border-gray-300 pl-10 pr-4 py-3 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>
          </div>

          {/* Observações Adicionais */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Observações adicionais
            </label>
            <textarea
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
              placeholder="Descreva mais detalhes sobre a barreira..."
              rows={4}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 resize-none"
            />
          </div>

          {/* Anexar Foto */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Anexar foto (opcional)
            </label>
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="relative border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors"
            >
              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/gif"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              {fotoPreview ? (
                <div className="space-y-2">
                  <img
                    src={fotoPreview}
                    alt="Preview"
                    className="mx-auto max-h-32 rounded-lg object-cover"
                  />
                  <p className="text-sm text-gray-600">{foto?.name}</p>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFoto(null);
                      setFotoPreview(null);
                    }}
                    className="text-sm text-red-600 hover:text-red-700"
                  >
                    Remover foto
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <span className="material-symbols-outlined text-4xl text-gray-400">
                    add_a_photo
                  </span>
                  <p className="text-sm text-gray-600">
                    Carregue um arquivo ou arraste e solte
                  </p>
                  <p className="text-xs text-gray-500">
                    PNG, JPG, GIF até 10MB
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Botões */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-700"
            >
              Enviar Reporte
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


