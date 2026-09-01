import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Result, Button } from 'antd'
import i18n from '../../i18n'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }
      return (
        <div className="p-8">
          <Result
            status="error"
            title={i18n.t('error.pageError')}
            subTitle={this.state.error?.message || i18n.t('error.unknownError')}
            extra={
              <Button type="primary" onClick={this.handleReset}>
                {i18n.t('error.retry')}
              </Button>
            }
          />
        </div>
      )
    }
    return this.props.children
  }
}
