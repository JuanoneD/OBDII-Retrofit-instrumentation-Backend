# 1. Etapa de Build
    FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
    WORKDIR /source
    
    # Copia e restaura dependências
    COPY *.csproj ./
    RUN dotnet restore
    
    # Copia o restante do código e compila
    COPY . .
    RUN dotnet publish -c Release -o /app/out
    
    # 2. Etapa de Execução (leve)
    FROM mcr.microsoft.com/dotnet/aspnet:8.0
    WORKDIR /app
    COPY --from=build /app/out .
    
    # No .NET 8+, a porta padrão interna é 5000
    ENV ASPNETCORE_HTTP_PORTS=5000
    EXPOSE 5000
    
    ENTRYPOINT ["dotnet", "OBDII-Backend.dll"]