import { useEffect, useState, useCallback } from 'react';
import { documentApi } from '../api/documents';
import type { Document } from '../types';
import { useDropzone } from 'react-dropzone';

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);

  const load = () => documentApi.listDocuments().then(setDocs);
  useEffect(() => { load(); }, []);

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    if (docs.find(d => d.filename === file.name)) {
      alert('该文件已存在');
      return;
    }
    setUploading(true);
    try {
      await documentApi.uploadDocument(file);
      await load();
    } catch (e) {
      alert('上传失败');
    }
    setUploading(false);
  }, [docs]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'], 'text/plain': ['.txt'] },
    maxFiles: 1,
  });

  const handleDelete = async (id: number) => {
    await documentApi.deleteDocument(id);
    await load();
  };

  return (
    <div className="p-4 h-full overflow-y-auto">
      <h2 className="text-lg font-medium mb-4" style={{ color: 'var(--color-text-primary)' }}>资料库</h2>

      <div
        {...getRootProps()}
        className="border-2 border-dashed rounded-xl p-8 mb-6 text-center cursor-pointer transition-colors"
        style={{
          borderColor: isDragActive ? 'var(--color-accent)' : 'var(--color-border)',
          backgroundColor: isDragActive ? 'var(--color-accent-light)' : 'var(--color-surface-alt)',
        }}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>上传中...</p>
        ) : isDragActive ? (
          <p className="text-sm" style={{ color: 'var(--color-accent)' }}>放开以上传文件</p>
        ) : (
          <div>
            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>拖放文件到此处，或点击选择</p>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>支持 PDF、DOCX、TXT</p>
          </div>
        )}
      </div>

      {docs.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>尚未上传任何文档</p>
        </div>
      ) : (
        <div className="border rounded-xl" style={{ borderColor: 'var(--color-border)' }}>
          {docs.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between px-4 py-3 border-b last:border-b-0"
              style={{ borderColor: 'var(--color-border)' }}
            >
              <div>
                <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{doc.filename}</div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                  {doc.chunk_count} 个片段 · {doc.content_type}
                </div>
              </div>
              <button
                onClick={() => handleDelete(doc.id)}
                className="text-xs cursor-pointer"
                style={{ color: 'var(--color-danger)' }}
              >
                删除
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
