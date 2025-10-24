import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const FileUpload = ({ onFileSelect, isLoading }) => {
  const [selectedFile, setSelectedFile] = useState(null)

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      setSelectedFile(file)
      onFileSelect(file)
    }
  }, [onFileSelect])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    maxFiles: 1,
    disabled: isLoading
  })

  const removeFile = () => {
    setSelectedFile(null)
  }

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-primary bg-primary/10'
            : 'border-primary/30 hover:border-primary/50 bg-secondary/50'
        } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          {isLoading ? (
            <>
              <Loader2 className="w-16 h-16 text-primary animate-spin" />
              <p className="text-lg font-medium text-text">Processing your trades...</p>
              <p className="text-sm text-text-dark">This may take a moment</p>
            </>
          ) : (
            <>
              <div className="bg-primary/10 p-4 rounded-full">
                <Upload className="w-12 h-12 text-primary" />
              </div>
              
              <div>
                <p className="text-lg font-medium text-text mb-2">
                  {isDragActive ? 'Drop your CSV file here' : 'Upload Trading CSV'}
                </p>
                <p className="text-sm text-text-dark">
                  Drag & drop or click to select a CSV file from Webull, TD, or Interactive Brokers
                </p>
              </div>

              <div className="flex items-center space-x-2 text-xs text-text-dark">
                <FileText className="w-4 h-4" />
                <span>Supported format: .csv</span>
              </div>
            </>
          )}
        </div>
      </div>

      <AnimatePresence>
        {selectedFile && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-4 bg-secondary border border-primary/20 rounded-lg p-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="bg-primary/10 p-2 rounded">
                  <FileText className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium text-text">{selectedFile.name}</p>
                  <p className="text-xs text-text-dark">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
              
              <button
                onClick={removeFile}
                className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-red-400" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default FileUpload
