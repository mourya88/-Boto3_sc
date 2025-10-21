apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: f2t-ccpromoapi-ingress
  namespace: f2t-ccpromoapi-xapi-tyk
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internal
    alb.ingress.kubernetes.io/target-type: instance
    alb.ingress.kubernetes.io/load-balancer-name: f2t-ccpromoapi-tyk-alb
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:eu-west-2:522814703639:certificate/80cfb446-4b13-4a60-98f5-9617055b5f21

    # Health check configuration
    alb.ingress.kubernetes.io/healthcheck-path: /accounts
    alb.ingress.kubernetes.io/healthcheck-protocol: HTTP
    alb.ingress.kubernetes.io/healthcheck-port: "traffic-port"
    alb.ingress.kubernetes.io/healthcheck-success-codes: "400"
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: "15"
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: "5"
    alb.ingress.kubernetes.io/healthy-threshold-count: "2"
    alb.ingress.kubernetes.io/unhealthy-threshold-count: "2"

spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - path: /accounts/*
            pathType: Prefix
            backend:
              service:
                name: ccpromoapi
                port:
                  number: 8080
          - path: /man/info/*
            pathType: Prefix
            backend:
              service:
                name: ccpromoapi
                port:
                  number: 8080
          - path: /accounts
            pathType: Prefix
            backend:
              service:
                name: ccpromoapi
                port:
                  number: 8080
